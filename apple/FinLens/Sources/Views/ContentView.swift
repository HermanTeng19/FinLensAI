import SwiftUI
import FinLensCore

struct ContentView: View {
    @Environment(AppViewModel.self) private var viewModel
    #if os(iOS)
    @Environment(\.horizontalSizeClass) private var horizontalSizeClass
    #endif

    var body: some View {
        #if os(macOS)
        MacRootView()
        #elseif os(iOS)
        if horizontalSizeClass == .regular {
            iPadRootView()
        } else {
            iOSRootView()
        }
        #endif
    }
}
