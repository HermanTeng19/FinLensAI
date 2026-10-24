import SwiftUI
import FinLensCore

@main
struct FinLensApp: App {
    @State private var appViewModel: AppViewModel

    init() {
        let initialTab: NavigationTab = CommandLine.arguments.contains("--tab-ask-ai") ? .askAI : .dashboard
        let vm = AppViewModel(initialTab: initialTab)
        if let promptIdx = CommandLine.arguments.firstIndex(of: "--prompt"),
           promptIdx + 1 < CommandLine.arguments.count {
            let prompt = CommandLine.arguments[promptIdx + 1]
            vm.askAIAssistant(prompt: prompt)
        }
        _appViewModel = State(initialValue: vm)
    }

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
