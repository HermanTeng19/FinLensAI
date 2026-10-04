import SwiftUI
import FinLensCore

#if os(macOS)
struct MacRootView: View {
    @Environment(AppViewModel.self) private var viewModel
    @State private var columnVisibility: NavigationSplitViewVisibility = .all

    var body: some View {
        @Bindable var vm = viewModel
        NavigationSplitView(columnVisibility: $columnVisibility) {
            List(NavigationTab.allCases, selection: Binding(
                get: { vm.selectedTab },
                set: { if let newTab = $0 { vm.selectTab(newTab) } }
            )) { tab in
                Label(tab.rawValue, systemImage: tab.systemImage)
                    .tag(tab)
            }
            .listStyle(.sidebar)
            .navigationTitle("FinLens AI")
        } detail: {
            TabSectionView(tab: vm.selectedTab)
                .toolbar {
                    ToolbarItemGroup(placement: .automatic) {
                        Button {
                            Task {
                                await vm.refresh()
                            }
                        } label: {
                            Label("Refresh", systemImage: "arrow.clockwise")
                        }
                        .keyboardShortcut("r", modifiers: .command)
                    }
                }
        }
        .frame(minWidth: 780, minHeight: 520)
    }
}
#endif
