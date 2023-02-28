import AppKit
import Foundation

class AppDelegate: NSObject, NSApplicationDelegate {

  var mainApp: NSRunningApplication? = nil

  func applicationWillFinishLaunching(_ notification: Notification) {
    // listen for notifications that an app was terminated, quit this app
    // if our main app is terminated
    NSWorkspace.shared.notificationCenter.addObserver(
      forName: NSWorkspace.didTerminateApplicationNotification,
      object: nil,  // always NSWorkspace
      queue: OperationQueue.main
    ) { [weak self] (notification: Notification) in
      if self?.mainApp?.isTerminated ?? false {
        NSApplication.shared.terminate(self)
      }
    }

    // now launch the main application
    // TODO: what name do we want? can you nest a bundle with the same name?
    let bundle = Bundle.main
    let bundleName = (bundle.bundleURL.lastPathComponent as NSString).deletingPathExtension
    let launchScript = bundle.url(forResource: bundleName, withExtension: "app")

    // TODO: only available on macOS 10.15+, do we need to support older?
    // https://developer.apple.com/documentation/appkit/nsworkspace/1532940-open
    let config = NSWorkspace.OpenConfiguration()
    // this allows multiple instances of napari to run, but we may not want that
    // config.createsNewApplicationInstance = true
    config.environment = ProcessInfo.processInfo.environment
    NSWorkspace.shared.openApplication(
      at: launchScript!,
      configuration: config,
      completionHandler: { [weak self] app, error in
        self?.mainApp = app
      }
    )
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
    // NSLog("MENUINST application open urls: \(urls)")
    self.mainApp?.activate(options: [.activateAllWindows, .activateIgnoringOtherApps])
    if let openURLScript = Bundle.main.url(forResource: "open-url", withExtension: nil) {
      do {
        let _ = try Process.run(
          openURLScript,
          // TODO: this default ("bad-input") is not great - should validate before we get here
          arguments: urls.map { $0.absoluteString.removingPercentEncoding ?? "bad-input" }
        )
        // p.waitUntilExit()  // TODO: might want/need to wait on this process
      } catch {}
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
