import SwiftUI

public enum InputType {
    case plain
    case email
    case password
}

public struct InputField: View {
    public let placeholder: String
    @Binding public var text: String
    public var type: InputType = .plain
    public var errorMessage: String?
    
    @State private var isSecure: Bool = true

    public init(_ placeholder: String, text: Binding<String>, type: InputType = .plain, errorMessage: String? = nil) {
        self.placeholder = placeholder
        self._text = text
        self.type = type
        self.errorMessage = errorMessage
    }

    public var body: some View {
        VStack(alignment: .leading, spacing: Spacing.xs) {
            Group {
                switch type {
                    case .plain:
                        TextField(placeholder, text: $text)
                    case .email:
                        TextField(placeholder, text: $text)
                            .keyboardType(.emailAddress)
                            .autocorrectionDisabled()
                            .autocapitalization(.none)
                            .textInputAutocapitalization(.none)
                    case .password:
                        ZStack(alignment: .trailing) {
                            if isSecure {
                                SecureField(placeholder, text: $text)
                                    .autocapitalization(.none)
                                    .disableAutocorrection(true)
                            } else {
                                TextField(placeholder, text: $text)
                                    .autocapitalization(.none)
                                    .disableAutocorrection(true)
                            }

                            Button(action: { isSecure.toggle() }) {
                                Image(systemName: isSecure ? "eye.slash" : "eye")
                                    .foregroundColor(Colors.onSurface.opacity(0.6))
                            }
                            .padding(.trailing, Spacing.sm)
                    }
                }
            }
            .font(Typography.body)
            .padding(Spacing.sm)
            .background(Colors.surface)
            .overlay(
                RoundedRectangle(cornerRadius: Radii.small)
                    .stroke(
                        errorMessage == nil
                            ? Colors.surface
                            : Colors.error,
                        lineWidth: 1
                    )
            )
            .cornerRadius(Radii.small)
            .shadow(
                color: Elevation.level1.color,
                radius: Elevation.level1.radius,
                x: Elevation.level1.x,
                y: Elevation.level1.y
            )

            if let error = errorMessage {
                Text(error)
                    .font(Typography.caption2)
                    .foregroundColor(Colors.error)
                    .padding(.horizontal, Spacing.sm)
            }
        }
    }
}
