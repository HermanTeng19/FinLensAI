import SwiftUI
import FinLensCore

#if os(iOS)
struct iOSRootView: View {
    @Environment(AppViewModel.self) private var viewModel

    var body: some View {
        @Bindable var vm = viewModel
        TabView(selection: $vm.selectedTab) {
            ForEach(NavigationTab.allCases) { tab in
                NavigationStack {
                    TabSectionView(tab: tab)
                }
                .tabItem {
                    Label(tab.rawValue, systemImage: tab.systemImage)
                }
                .tag(tab)
            }
        }
    }
}
#endif
