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
will send call the `handle-url` script placed under Resources. This script will
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
import Darwin
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
        fputs("Main app finished. Wrapper will terminate\n", stderr)
        NSApplication.shared.terminate(self)
      }
    }

    let env = ProcessInfo.processInfo.environment
    // TODO: only available on macOS 10.15+, do we need to support older?
    // https://developer.apple.com/documentation/appkit/nsworkspace/1532940-open
    let config = NSWorkspace.OpenConfiguration()
    config.createsNewApplicationInstance = env.keys.contains("MENUINST_ALLOW_MULTIPLE_INSTANCES")
    config.environment = env

    os_log("Opening app %@", log: self.osLog, type: .debug, self.wrappedApp()!.absoluteString)
    fputs("Opening app \(self.wrappedApp()!.absoluteString)\n", stderr)
    NSWorkspace.shared.openApplication(
      at: self.wrappedApp()!,
      configuration: config,
      completionHandler: { [weak self] app, error in
        self?.mainApp = app
      }
    )
    os_log("Opened app %@", log: self.osLog, type: .debug, self.wrappedApp()!.absoluteString)
    fputs("Opened app \(self.wrappedApp()!.absoluteString)\n", stderr)
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
    // convert the urls to strings and pass them to the main app via `handle-url`
    os_log("%s will open urls: %@", log: self.osLog, type: .debug, self.wrappedScript()!.absoluteString, urls)
    fputs("\(self.wrappedScript()!.absoluteString) will open urls: \(urls)\n", stderr)
    self.mainApp?.activate(options: [.activateAllWindows, .activateIgnoringOtherApps])
    if let openURLScript = Bundle.main.url(forResource: "handle-url", withExtension: nil) {
      do {
        let process = try Process.run(
          openURLScript,
          // TODO: this default ("bad-input") is not great - should validate before we get here
          arguments: urls.map { $0.absoluteString.removingPercentEncoding ?? "bad-input" }
        )
        // process.waitUntilExit()  // TODO: might want/need to wait on this process
      } catch {
          os_log("Could not handle URLs: %@", log: self.osLog, type: .error, urls)
          fputs("Could not handle URLs: \(urls)\n", stderr)
      }
    } else {
      os_log("Could not find `handle-url` script under Resources", log: self.osLog, type: .error)
      fputs("Could not find `handle-url` script under Resources\n", stderr)
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
