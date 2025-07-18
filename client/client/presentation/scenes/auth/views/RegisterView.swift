import SwiftUI

struct RegisterView: View {
    @Environment(\.presentationMode) var presentationMode
    @State private var username: String = ""
    @State private var email: String = ""
    @State private var password: String = ""
    @State private var confirmPassword: String = ""
    
    private func handleBackPress() {
        presentationMode.wrappedValue.dismiss()
    }
    
    private func validateEmail(_ email: String) -> String? {
        return nil
    }
    
    private func validateUsername(_ username: String) -> String? {
        return nil
    }
    
    private func validatePassword(_ password: String) -> String? {
        return nil
    }
    
    var body: some View {
        VStack() {
            Title(
                "Create Account",
                alignment: .leading,
                showBackButton: true,
                backButtonAction: handleBackPress
            )
            
            VStack(spacing: AppSpacing.Semantic.input) {
                CustomTextField(
                    "Username",
                    text: $username,
                    validation: validateUsername
                )
                
                CustomTextField(
                    "Email",
                    text: $email,
                    keyboardType: .emailAddress,
                    validation: validateEmail
                )
                
                HStack(spacing: AppSpacing.Semantic.input) {
                    CustomTextField(
                        "Password",
                        text: $password,
                        isSecure: true,
                        validation: validatePassword
                    )
                    
                    CustomTextField(
                        "Password",
                        text: $password,
                        isSecure: true,
                        validation: validatePassword
                    )
                }
            }.padding(.horizontal, AppSpacing.lg)
            
            Spacer()
            
            Button(action: handleBackPress) {
                Text("Create Account")
                    .fontWeight(.bold)
                    .frame(maxWidth: .infinity)
                    .frame(height: AppSizing.Semantic.button)
                    .foregroundColor(.white)
            }
            .background(Color.blue)
            .cornerRadius(AppRadius.Semantic.button)
            .padding(.horizontal, AppSpacing.Semantic.screen)
            .padding(.bottom, AppSpacing.Semantic.screen)
        }
    }
}

#Preview {
    RegisterView()
}
