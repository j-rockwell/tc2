import SwiftUI

struct LoginView: View {
    @Environment(\.presentationMode) var presentationMode
    @State private var username: String = ""
    @State private var password: String = ""
    
    private func handleBackPress() {
        presentationMode.wrappedValue.dismiss()
    }
    
    private func handleSignInPress() {
        print("sign in press")
    }
    
    var body: some View {
        VStack() {
            Title(
                "Sign in",
                alignment: .leading,
                showBackButton: true,
                backButtonAction: handleBackPress
            )
            
            VStack(spacing: AppSpacing.Semantic.input) {
                CustomTextField(
                    "Email or Username",
                    text: $username,
                )
                
                CustomTextField(
                    "Password",
                    text: $password,
                    isSecure: true,
                )
            }
            .padding(.horizontal, AppSpacing.Semantic.screen)
            
            Spacer()
            
            VStack(spacing: AppSpacing.Semantic.element) {
                NavigationLink(destination: ForgotPasswordView().navigationBarBackButtonHidden(true)) {
                    Button(action: {}) {
                        Text("Forgot Password")
                            .fontWeight(.bold)
                            .frame(maxWidth: .infinity)
                            .frame(height: AppSizing.Semantic.button)
                            .foregroundColor(.white)
                    }
                    .background(Color.gray)
                    .cornerRadius(AppRadius.Semantic.button)
                }
                
                Button(action: handleSignInPress) {
                    Text("Sign in")
                        .fontWeight(.bold)
                        .frame(maxWidth: .infinity)
                        .frame(height: AppSizing.Semantic.button)
                        .foregroundColor(.white)
                }
                .background(Color.blue)
                .cornerRadius(AppRadius.Semantic.button)
            }
            .padding(.bottom, AppSpacing.Semantic.screen)
            .padding(.horizontal, AppSpacing.Semantic.screen)
        }
    }
}

#Preview {
    LoginView()
}
