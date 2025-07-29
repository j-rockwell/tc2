import SwiftUI

public struct PrimaryButtonStyle: ButtonStyle {
    public func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(Typography.body)
            .foregroundColor(Colors.onPrimary)
            .padding(.vertical, Spacing.sm)
            .frame(maxWidth: .infinity)
            .background(Colors.primary)
            .cornerRadius(Radii.medium)
            .shadow(color: Elevation.level1.color,
                    radius: Elevation.level1.radius,
                    x: Elevation.level1.x,
                    y: Elevation.level1.y)
            .opacity(configuration.isPressed ? 0.8 : 1)
    }
}

public struct SecondaryButtonStyle: ButtonStyle {
    public func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(Typography.body)
            .foregroundColor(Colors.primary)
            .padding(.vertical, Spacing.sm)
            .frame(maxWidth: .infinity)
            .background(Colors.surface)
            .overlay(
                RoundedRectangle(cornerRadius: Radii.medium)
                    .stroke(Colors.primary, lineWidth: 1)
            )
            .cornerRadius(Radii.medium)
            .shadow(color: Elevation.level1.color,
                    radius: Elevation.level1.radius,
                    x: Elevation.level1.x,
                    y: Elevation.level1.y)
            .opacity(configuration.isPressed ? 0.8 : 1)
    }
}
