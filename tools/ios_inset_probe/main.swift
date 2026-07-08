// Tiny simulator-only probe: prints the real safe-area insets (in points)
// and exits. The ios-simulator workflow runs it on the device matrix and
// compares the output against tests/ios_inset_fixtures.txt, so the numbers
// that drive the portrait layout math stay honest without owning an iPhone.
import UIKit

class ProbeViewController: UIViewController {
    override func viewDidAppear(_ animated: Bool) {
        super.viewDidAppear(animated)
        // One runloop beat so the window has final insets.
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            let insets = self.view.window?.safeAreaInsets ?? .zero
            let bounds = UIScreen.main.bounds
            print("INSET_PROBE \(Int(bounds.width))x\(Int(bounds.height)) " +
                  "top=\(Int(insets.top)) bottom=\(Int(insets.bottom))")
            fflush(stdout)
            exit(0)
        }
    }
}

class AppDelegate: UIResponder, UIApplicationDelegate {
    var window: UIWindow?

    func application(_ application: UIApplication,
                     didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
        window = UIWindow(frame: UIScreen.main.bounds)
        window?.rootViewController = ProbeViewController()
        window?.makeKeyAndVisible()
        // Belt and braces: never leave the workflow hanging on a stuck app.
        DispatchQueue.main.asyncAfter(deadline: .now() + 10) {
            print("INSET_PROBE_TIMEOUT")
            fflush(stdout)
            exit(2)
        }
        return true
    }
}

_ = UIApplicationMain(CommandLine.argc, CommandLine.argv, nil, NSStringFromClass(AppDelegate.self))
