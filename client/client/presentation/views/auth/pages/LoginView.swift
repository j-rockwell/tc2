import SwiftUI

struct LoginView: View {
    @State private var email = ""
    @State private var password = ""
    
    var body: some View {
        VStack {
            VStack(spacing: Spacing.Semantic.inputGroup) {
                InputField("Email", text: $email, type: .email, errorMessage: nil)
                InputField("Password", text: $password, type: .password, errorMessage: nil)
            }
            
            Spacer()
            
            VStack(spacing: Spacing.Semantic.buttonGroup) {
                Button("Sign in", action: {}).buttonStyle(PrimaryButtonStyle())
                Button("Forgot Password", action: {}).buttonStyle(SecondaryButtonStyle())
            }
        }.padding()
    }
}

#Preview {
    LoginView()
}
