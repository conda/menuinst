/*
macOS launcher to process URLs and custom file types for menuinst shortcuts.

It uses swift to register the required protocols and pass event payloads to the
actual shortcut executable as command line arguments.

Let's define two apps:

- The swift launcher app, which is a wrapper around the actual shortcut app
- The shortcut app, which includes a C launcher that is the actual entry point
  for the shortcut

The swift launcher will open the shortcut app (bundled as a Resource) and then
will stay open "listening" for more macOS events. When it receives an event, it
will send call the `handle-event` script placed under Resources. This script will
be given the event payload as a command line argument. It can then do whatever;
some examples:

- send the event payload to a socket via `nc`
- send the event payload to a URL via curl
- write to a file and let the app get notified via inotify or similar
- ... you get the idea

References:
- https://developer.apple.com/documentation/xcode/defining-a-custom-url-scheme-for-your-app

Authors, 2023
- Ashley Anderson (@aganders3)
- Jaime Rodríguez-Guerra (@jaimergp)
*/

import AppKit
import Foundation
import os.log

class AppDelegate: NSObject, NSApplicationDelegate {
  var osLog: OSLog = OSLog(subsystem: "org.conda.menuinst", category: "menuinst")
  var mainApp: NSRunningApplication? = nil

  func wrappedApp()->URL? {
      let bundle = Bundle.main
      let bundleName = (bundle.bundleURL.lastPathComponent as NSString).deletingPathExtension
      return bundle.url(forResource: bundleName, withExtension: "app")
  }

  func wrappedScript()->URL? {
      let bundle = Bundle.main
      let bundleName = (bundle.bundleURL.lastPathComponent as NSString).deletingPathExtension
      let bundleURL = bundle.url(forResource: bundleName, withExtension: "app")
      return (
        bundleURL!
        .appendingPathComponent("Contents")
        .appendingPathComponent("MacOS")
        .appendingPathComponent(bundleName)
      )
  }

  func applicationWillFinishLaunching(_ notification: Notification) {
    // listen for notifications that an app was terminated, quit this app
    // if our main app is terminated
    NSWorkspace.shared.notificationCenter.addObserver(
      forName: NSWorkspace.didTerminateApplicationNotification,
      object: nil,  // always NSWorkspace
      queue: OperationQueue.main
    ) { [weak self] (notification: Notification) in
      if self?.mainApp?.isTerminated ?? false {
        os_log("Main app finished. Wrapper will terminate", log: self!.osLog, type: .debug)
        NSApplication.shared.terminate(self)
      }
    }

    os_log("Opening app %@", log: self.osLog, type: .debug, self.wrappedApp()!.absoluteString)
    let env = ProcessInfo.processInfo.environment
    if #available(macOS 10.15, *) {
      let config = NSWorkspace.OpenConfiguration()
      config.environment = env
      config.createsNewApplicationInstance = env.keys.contains("MENUINST_ALLOW_MULTIPLE_INSTANCES")

      NSWorkspace.shared.openApplication(
        at: self.wrappedApp()!,
        configuration: config,
        completionHandler: { [weak self] app, error in
          self?.mainApp = app
        }
      )
    } else {
      // Fallback on earlier versions (>=10.6,<10.15)
      var options: NSWorkspace.LaunchOptions = []
      if env.keys.contains("MENUINST_ALLOW_MULTIPLE_INSTANCES") {
        options.insert(.newInstance)
      }
      let app = try! NSWorkspace.shared.launchApplication(
        at: self.wrappedApp()!,
        options: options,
        configuration: [NSWorkspace.LaunchConfigurationKey.environment: env]
      )
    }
    os_log("Opened app %@", log: self.osLog, type: .debug, self.wrappedApp()!.absoluteString)
  }

  func applicationShouldHandleReopen(_ sender: NSApplication, hasVisibleWindows flag: Bool) -> Bool
  {
    // this is called when a user tries to reopen the app (e.g. by
    // double-clicking the icon even though it's already running) so we
    // activate the main app and return false to ignore the reopen request
    // if you return true, it AppKit will call the rest of the "open
    // untitled document" flow:
    // applicationShouldOpenUntitledFile(_:) -> applicationOpenUntitledFile(_:)
    self.mainApp?.activate(options: [.activateAllWindows, .activateIgnoringOtherApps])
    return false
  }

  func application(_ application: NSApplication, open urls: [URL]) {
    // convert the urls to strings and pass them to the main app via `handle-event`
    os_log("%s will open urls: %@", log: self.osLog, type: .debug, self.wrappedScript()!.absoluteString, urls)
    self.mainApp?.activate(options: [.activateAllWindows, .activateIgnoringOtherApps])
    if let openURLScript = Bundle.main.url(forResource: "handle-event", withExtension: nil) {
      do {
        let process = try Process.run(
          openURLScript,
          // TODO: this default ("bad-input") is not great - should validate before we get here
          arguments: urls.map { $0.absoluteString.removingPercentEncoding ?? "bad-input" }
        )
        // process.waitUntilExit()  // TODO: might want/need to wait on this process
      } catch {
          os_log("Could not handle URLs: %@", log: self.osLog, type: .error, urls)
      }
    } else {
      os_log("Could not find `handle-event` script under Resources", log: self.osLog, type: .error)
    }
  }
}

@main
struct SwiftLauncher {
  public static func main() {
    let app = NSApplication.shared
    let delegate = AppDelegate()
    app.delegate = delegate
    app.run()
  }
}
