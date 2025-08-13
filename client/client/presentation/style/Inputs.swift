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

struct TimeInput: View {
    @Binding var seconds: Int
    
    @State private var hoursText = "0"
    @State private var minutesText = "00"
    @State private var secondsText = "00"
    
    var body: some View {
        HStack {
            
        }
    }
    
    @ViewBuilder
    private func numberField(_ text: Binding<String>, placeholder: String, max: Int?, padTo2: Bool = false) -> some View {
        TextField(placeholder, text: text)
            .keyboardType(.numberPad)
            .multilineTextAlignment(.trailing)
            .frame(minWidth: padTo2 ? 36 : 24)
            .onChange(of: text.wrappedValue) {
                var filtered = text.wrappedValue.filter(\.isNumber)
                if filtered.isEmpty { filtered = "0" }
                if let max, let n = Int(filtered) { filtered = String(min(max, n)) }
                if text.wrappedValue != filtered { text.wrappedValue = filtered }

                seconds = componentsToSeconds(
                    TimeComponents(
                        hours: Int(hoursText) ?? 0,
                        minutes: Int(minutesText) ?? 0,
                        seconds: Int(secondsText) ?? 0
                    )
                )
            }
            .onSubmit {
                normalizeAndPush()
            }
    }
    
    private func normalizeAndPush() {
        let h = max(0, Int(hoursText) ?? 0)
        let m = max(0, min(59, Int(minutesText) ?? 0))
        let s = max(0, min(59, Int(secondsText) ?? 0))
        hoursText = String(h)
        minutesText = String(format: "%02d", m)
        secondsText = String(format: "%02d", s)
        seconds = componentsToSeconds(TimeComponents(hours: h, minutes: m, seconds: s))
    }
}
