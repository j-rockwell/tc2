import SwiftUI
import UIKit

struct AppRadius {
    static let none: CGFloat = 0
    static let xs: CGFloat = 2
    static let sm: CGFloat = 4
    static let md: CGFloat = 6
    static let lg: CGFloat = 8
    static let xl: CGFloat = 12
    static let xl2: CGFloat = 16
    static let xl3: CGFloat = 24
    static let full: CGFloat = 9999
    
    struct Semantic {
        static let button = AppRadius.lg
        static let card = AppRadius.xl
        static let input = AppRadius.lg
        static let modal = AppRadius.xl2
        static let image = AppRadius.md
    }
}
