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
                    appViewModel.isShowingFileImporter = true
                }
                .keyboardShortcut("o", modifiers: .command)
            }

            CommandMenu("Navigation") {
                Button("Dashboard") {
                    appViewModel.selectTab(.dashboard)
                }
                .keyboardShortcut("1", modifiers: .command)

                Button("Transactions") {
                    appViewModel.selectTab(.transactions)
                }
                .keyboardShortcut("2", modifiers: .command)

                Button("AI Insights") {
                    appViewModel.selectTab(.insights)
                }
                .keyboardShortcut("3", modifiers: .command)

                Button("Ask AI Assistant") {
                    appViewModel.selectTab(.askAI)
                }
                .keyboardShortcut("4", modifiers: .command)

                Button("Statements & Privacy") {
                    appViewModel.selectTab(.profile)
                }
                .keyboardShortcut("5", modifiers: .command)
            }

            CommandMenu("Data") {
                Button("Refresh All Data") {
                    Task {
                        await appViewModel.refresh()
                    }
                }
                .keyboardShortcut("r", modifiers: .command)
            }
        }
        #endif
    }
}
