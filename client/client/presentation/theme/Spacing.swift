import SwiftUI
import UIKit

struct AppSpacing {
    static let baseUnit: CGFloat = 4
    
    static let none: CGFloat = 0
    static let xs: CGFloat = baseUnit * 1      // 4pt
    static let sm: CGFloat = baseUnit * 2      // 8pt
    static let md: CGFloat = baseUnit * 3      // 12pt
    static let lg: CGFloat = baseUnit * 4      // 16pt
    static let xl: CGFloat = baseUnit * 5      // 20pt
    static let xl2: CGFloat = baseUnit * 6     // 24pt
    static let xl3: CGFloat = baseUnit * 8     // 32pt
    static let xl4: CGFloat = baseUnit * 10    // 40pt
    static let xl5: CGFloat = baseUnit * 12    // 48pt
    static let xl6: CGFloat = baseUnit * 16    // 64pt
    static let xl7: CGFloat = baseUnit * 20    // 80pt
    static let xl8: CGFloat = baseUnit * 24    // 96pt
    
    struct Semantic {
        static let element = AppSpacing.sm     // Gap between related elements
        static let section = AppSpacing.lg     // Gap between sections
        static let screen = AppSpacing.lg      // Screen edge padding
        static let card = AppSpacing.lg        // Card internal padding
        static let button = AppSpacing.md      // Button internal padding
        static let input = AppSpacing.lg       // Input field padding
    }
}
