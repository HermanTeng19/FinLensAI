import SwiftUI
import FinLensCore

@main
struct FinLensApp: App {
    @State private var appViewModel = AppViewModel()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environment(appViewModel)
        }
        #if os(macOS)
        .commands {
            SidebarCommands()
            CommandGroup(replacing: .newItem) {
                Button("Import Statement...") {
                    // Handled in Phase 3
                }
                .keyboardShortcut("o", modifiers: .command)
            }
        }
        #endif
    }
}
