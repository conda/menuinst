import AppKit
import Foundation

class AppDelegate: NSObject, NSApplicationDelegate {

    var mainApp: NSRunningApplication? = nil

    func applicationWillFinishLaunching(_ notification: Notification) {
        // listen for notifications that an app was terminated, quit this app
        // if our main app is terminated
        NSWorkspace.shared.notificationCenter.addObserver(
            forName: NSWorkspace.didTerminateApplicationNotification,
            object: nil, // always NSWorkspace
            queue: OperationQueue.main
        ) { [weak self] (notification: Notification) in
            if (self?.mainApp?.isTerminated ?? false) {
                NSApplication.shared.terminate(self)
            }
        }

        // now launch the main application
        // TODO: what name do we want? can you nest a bundle with the same name?
        let bundle = Bundle.main
        // let bundleName = bundle.infoDictionary!["CFBundleDisplayName"] as! String
        let bundleName = (bundle.bundleURL.lastPathComponent as NSString).deletingPathExtension
        let launchScript = bundle.url(forResource: bundleName, withExtension: "app")
        // TODO: only available on macOS 10.15+, do we need to support older?
        // https://developer.apple.com/documentation/appkit/nsworkspace/1532940-open
        let config = NSWorkspace.OpenConfiguration()
        // this allows multiple instances of napari to run, but we may not want that
        // config.createsNewApplicationInstance = true
        NSWorkspace.shared.openApplication(
            at: launchScript!,
            configuration: config,
            completionHandler: { [weak self] app, error in
                self?.mainApp = app
            }
        )
    }

    func applicationWillBecomeActive(_ notification: Notification) {
        // NSLog("MENUINST applicationWillBecomeActive activation policy: \(NSApp.activationPolicy())")
        // TODO: figure out why we need to hide the application icon again -
        // even with this it still flashes very quickly
        NSApp.setActivationPolicy(.accessory)
        // this brings the app to the front if the user re-opens it and when
        // opening another URL
        self.mainApp?.activate(options: [.activateAllWindows, .activateIgnoringOtherApps])
    }

    func application(_ application: NSApplication, open urls: [URL]) {
        // NSLog("MENUINST application open urls: \(urls)")
        // self.mainApp?.activate(options: [.activateAllWindows, .activateIgnoringOtherApps])
        if let open_url_script = Bundle.main.url(forResource: "open-url", withExtension: nil) {
            do {
                let _ = try Process.run(
                    open_url_script,
                    arguments: urls.map { $0.absoluteString.removingPercentEncoding ?? "bad-input"}
                )
                // p.waitUntilExit()  // TODO: might not want/need to wait on this process
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
        // hide the application icon in the dock - this seems to work just as
        // well as the Info.plist entry
        app.setActivationPolicy(.accessory)
        app.run()
    }
}
