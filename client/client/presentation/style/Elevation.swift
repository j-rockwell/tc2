import SwiftUI

public struct Shadow {
    public let color: Color
    public let radius: CGFloat
    public let x: CGFloat
    public let y: CGFloat
}

public enum Elevation {
    public static let level1 = Shadow(color: Color.black.opacity(0.05), radius: 1, x: 0, y: 1)
    public static let level2 = Shadow(color: Color.black.opacity(0.1), radius: 4, x: 0, y: 2)
    public static let level3 = Shadow(color: Color.black.opacity(0.15), radius: 6, x: 0, y: 4)
}
