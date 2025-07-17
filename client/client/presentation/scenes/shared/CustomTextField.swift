import SwiftUI

struct CustomTextField: View {
    let title: String
    @Binding var text: String
    let isSecure: Bool
    let keyboardType: UIKeyboardType
    let validation: ((String) -> String?)?
    
    @State private var isEditing = false
    @State private var validationMessage: String?
    
    init(
        _ title: String,
        text: Binding<String>,
        isSecure: Bool = false,
        keyboardType: UIKeyboardType = .default,
        validation: ((String) -> String?)? = nil
    ) {
        self.title = title
        self._text = text
        self.isSecure = isSecure
        self.keyboardType = keyboardType
        self.validation = validation
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            ZStack(alignment: .leading) {
                Rectangle()
                    .fill(Color(.systemGray6))
                    .frame(height: AppSizing.Semantic.button)
                    .cornerRadius(AppRadius.Semantic.input)
                    .overlay(
                        RoundedRectangle(cornerRadius: AppRadius.Semantic.input)
                            .stroke(borderColor, lineWidth: 1)
                    )
                
                HStack {
                    VStack(alignment: .leading, spacing: 2) {
                        if isEditing || !text.isEmpty {
                            Text(title)
                                .font(.caption)
                                .foregroundColor(.secondary)
                                .transition(.opacity)
                        }
                        
                        if isSecure {
                            SecureField(isEditing || !text.isEmpty ? "" : title, text: $text)
                                .textFieldStyle(PlainTextFieldStyle())
                        } else {
                            TextField(isEditing || !text.isEmpty ? "" : title, text: $text)
                                .keyboardType(keyboardType)
                                .textFieldStyle(PlainTextFieldStyle())
                        }
                    }
                    .padding(.horizontal, 16)
                    .padding(.vertical, 8)
                    
                    Spacer()
                }
            }
            .onTapGesture {
                isEditing = true
            }
            .onChange(of: text) { newValue in
                validateInput(newValue)
            }
            
            if let validationMessage = validationMessage {
                Text(validationMessage)
                    .font(.caption)
                    .foregroundColor(.red)
                    .transition(.opacity)
            }
        }
        .animation(.easeInOut(duration: 0.2), value: isEditing)
        .animation(.easeInOut(duration: 0.2), value: validationMessage)
    }
    
    private var borderColor: Color {
        if let validationMessage = validationMessage, !validationMessage.isEmpty {
            return .red
        }
        return isEditing ? .blue : Color(.systemGray4)
    }
    
    private func validateInput(_ input: String) {
        if let validation = validation {
            validationMessage = validation(input)
        }
    }
}
