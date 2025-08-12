import Foundation

class ParticipantColorGenerator {
    static func generateParticipantColor() -> String {
        let colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", "#DDA0DD", "#FF9FF3", "#54A0FF"]
        return colors.randomElement() ?? "#FFFFFF"
    }
}
