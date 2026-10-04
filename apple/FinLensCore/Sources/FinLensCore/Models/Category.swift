import Foundation

public struct Category: Identifiable, Sendable, Codable, Equatable, Hashable {
    public let id: String
    public let name: String
    public let iconName: String
    public let isSystemDefault: Bool

    public init(id: String, name: String, iconName: String, isSystemDefault: Bool = true) {
        self.id = id
        self.name = name
        self.iconName = iconName
        self.isSystemDefault = isSystemDefault
    }
}

public extension Category {
    static let defaults: [Category] = [
        Category(id: "Housing", name: "Housing", iconName: "house"),
        Category(id: "Food", name: "Food", iconName: "fork.knife"),
        Category(id: "Transportation", name: "Transportation", iconName: "car"),
        Category(id: "Shopping", name: "Shopping", iconName: "cart"),
        Category(id: "Entertainment", name: "Entertainment", iconName: "tv"),
        Category(id: "Healthcare", name: "Healthcare", iconName: "cross.case"),
        Category(id: "Utilities", name: "Utilities", iconName: "bolt"),
        Category(id: "Travel", name: "Travel", iconName: "airplane"),
        Category(id: "Education", name: "Education", iconName: "book"),
        Category(id: "Financial", name: "Financial", iconName: "banknote"),
        Category(id: "Income", name: "Income", iconName: "arrow.down.circle"),
        Category(id: "Transfer", name: "Transfer", iconName: "arrow.left.arrow.right"),
        Category(id: "Other", name: "Other", iconName: "ellipsis.circle")
    ]
}
