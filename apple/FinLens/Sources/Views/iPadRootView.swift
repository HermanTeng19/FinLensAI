import SwiftUI
import FinLensCore

#if os(iOS)
struct iPadRootView: View {
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
            .navigationTitle("FinLens AI")
        } detail: {
            NavigationStack {
                TabSectionView(tab: vm.selectedTab)
            }
        }
    }
}
#endif
