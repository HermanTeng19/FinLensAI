// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "FinLensCore",
    platforms: [
        .iOS(.v17),
        .macOS(.v14)
    ],
    products: [
        .library(
            name: "FinLensCore",
            targets: ["FinLensCore"]
        ),
    ],
    targets: [
        .target(
            name: "FinLensCore",
            dependencies: [],
            path: "Sources/FinLensCore"
        ),
        .testTarget(
            name: "FinLensCoreTests",
            dependencies: ["FinLensCore"],
            path: "Tests/FinLensCoreTests"
        ),
    ]
)
