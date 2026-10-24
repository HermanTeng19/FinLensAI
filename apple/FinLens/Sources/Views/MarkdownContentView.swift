import SwiftUI

/// MarkdownContentView: Renders structured Markdown with inline styling (bold, italic, code, links),
/// headers, bullet lists, numbered lists, blockquotes, and severity pill badges.
/// Fully compatible with iOS, iPadOS, and macOS across Dynamic Type and Dark/Light modes.
struct MarkdownContentView: View {
    let content: String

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            ForEach(Array(parseElements(content).enumerated()), id: \.offset) { _, element in
                switch element {
                case .heading(let level, let text):
                    Text(LocalizedStringKey(text))
                        .font(headingFont(for: level))
                        .bold()
                        .foregroundStyle(.primary)
                        .padding(.top, level == 1 ? 4 : 2)
                        .textSelection(.enabled)

                case .bullet(let text):
                    HStack(alignment: .top, spacing: 6) {
                        Text("•")
                            .font(.body)
                            .foregroundStyle(Color.accentColor)
                            .accessibilityHidden(true)

                        if let (severity, rest) = extractSeverity(text) {
                            HStack(alignment: .top, spacing: 6) {
                                severityBadge(for: severity)
                                Text(LocalizedStringKey(rest))
                                    .font(.body)
                                    .foregroundStyle(.primary)
                                    .textSelection(.enabled)
                            }
                        } else {
                            Text(LocalizedStringKey(text))
                                .font(.body)
                                .foregroundStyle(.primary)
                                .textSelection(.enabled)
                        }
                    }

                case .numbered(let num, let text):
                    HStack(alignment: .top, spacing: 6) {
                        Text("\(num).")
                            .font(.body.monospacedDigit().bold())
                            .foregroundStyle(.secondary)
                            .accessibilityLabel("Step \(num)")

                        Text(LocalizedStringKey(text))
                            .font(.body)
                            .foregroundStyle(.primary)
                            .textSelection(.enabled)
                    }

                case .codeBlock(let code):
                    ScrollView(.horizontal, showsIndicators: false) {
                        Text(code)
                            .font(.system(.callout, design: .monospaced))
                            .foregroundStyle(.primary)
                            .padding(10)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }
                    .background(RoundedRectangle(cornerRadius: 8).fill(Color.secondary.opacity(0.12)))
                    .textSelection(.enabled)

                case .blockquote(let text):
                    HStack(alignment: .top, spacing: 8) {
                        RoundedRectangle(cornerRadius: 1.5)
                            .fill(Color.accentColor)
                            .frame(width: 3)
                            .accessibilityHidden(true)

                        Text(LocalizedStringKey(text))
                            .font(.body)
                            .italic()
                            .foregroundStyle(.secondary)
                            .textSelection(.enabled)
                    }
                    .padding(.vertical, 2)

                case .paragraph(let text):
                    if text.trimmingCharacters(in: .whitespaces).isEmpty {
                        Spacer().frame(height: 4)
                    } else if let (severity, rest) = extractSeverity(text) {
                        HStack(alignment: .top, spacing: 6) {
                            severityBadge(for: severity)
                            Text(LocalizedStringKey(rest))
                                .font(.body)
                                .foregroundStyle(.primary)
                                .textSelection(.enabled)
                        }
                    } else {
                        Text(LocalizedStringKey(text))
                            .font(.body)
                            .foregroundStyle(.primary)
                            .textSelection(.enabled)
                    }
                }
            }
        }
    }

    private func headingFont(for level: Int) -> Font {
        switch level {
        case 1: return .title2
        case 2: return .title3
        case 3: return .headline
        default: return .subheadline
        }
    }

    private func extractSeverity(_ text: String) -> (String, String)? {
        let trimmed = text.trimmingCharacters(in: .whitespaces)
        for sev in ["HIGH", "MEDIUM", "LOW", "CRITICAL", "INFO"] {
            let tag = "[\(sev)]"
            if trimmed.hasPrefix(tag) {
                let rest = String(trimmed.dropFirst(tag.count)).trimmingCharacters(in: .whitespaces)
                return (sev, rest)
            }
        }
        return nil
    }

    @ViewBuilder
    private func severityBadge(for severity: String) -> some View {
        let color: Color = switch severity {
        case "HIGH", "CRITICAL": .red
        case "MEDIUM": .orange
        case "LOW": .blue
        default: .secondary
        }

        Text(severity)
            .font(.system(size: 10, weight: .bold))
            .foregroundStyle(color)
            .padding(.horizontal, 6)
            .padding(.vertical, 2)
            .background(Capsule().fill(color.opacity(0.15)))
    }

    enum Element {
        case heading(level: Int, text: String)
        case bullet(text: String)
        case numbered(num: String, text: String)
        case codeBlock(code: String)
        case blockquote(text: String)
        case paragraph(text: String)
    }

    private func parseElements(_ raw: String) -> [Element] {
        let lines = raw.components(separatedBy: "\n")
        var elements: [Element] = []
        var inCodeBlock = false
        var codeBlockLines: [String] = []

        for line in lines {
            let trimmed = line.trimmingCharacters(in: .whitespaces)

            // Code block delimiter
            if trimmed.hasPrefix("```") {
                if inCodeBlock {
                    elements.append(.codeBlock(code: codeBlockLines.joined(separator: "\n")))
                    codeBlockLines = []
                    inCodeBlock = false
                } else {
                    inCodeBlock = true
                    codeBlockLines = []
                }
                continue
            }

            if inCodeBlock {
                codeBlockLines.append(line)
                continue
            }

            // Headings
            if trimmed.hasPrefix("### ") {
                elements.append(.heading(level: 3, text: String(trimmed.dropFirst(4))))
            } else if trimmed.hasPrefix("## ") {
                elements.append(.heading(level: 2, text: String(trimmed.dropFirst(3))))
            } else if trimmed.hasPrefix("# ") {
                elements.append(.heading(level: 1, text: String(trimmed.dropFirst(2))))
            // Blockquotes
            } else if trimmed.hasPrefix("> ") {
                elements.append(.blockquote(text: String(trimmed.dropFirst(2))))
            // Bullet Lists
            } else if trimmed.hasPrefix("- ") || trimmed.hasPrefix("* ") {
                elements.append(.bullet(text: String(trimmed.dropFirst(2))))
            // Numbered Lists
            } else if let match = matchNumberedList(trimmed) {
                elements.append(.numbered(num: match.num, text: match.text))
            // Standard Paragraph
            } else {
                elements.append(.paragraph(text: line))
            }
        }

        // Handle unclosed code block gracefully
        if inCodeBlock && !codeBlockLines.isEmpty {
            elements.append(.codeBlock(code: codeBlockLines.joined(separator: "\n")))
        }

        return elements
    }

    private func matchNumberedList(_ line: String) -> (num: String, text: String)? {
        guard let dotIndex = line.firstIndex(of: ".") else { return nil }
        let prefix = line[..<dotIndex]
        if Int(prefix) != nil, line.index(after: dotIndex) < line.endIndex, line[line.index(after: dotIndex)] == " " {
            let text = String(line[line.index(dotIndex, offsetBy: 2)...])
            return (String(prefix), text)
        }
        return nil
    }
}
