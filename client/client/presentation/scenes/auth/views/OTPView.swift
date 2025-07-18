import SwiftUI

struct OTPView: View {
    @State private var username: String = ""
    
    private func handleBackPress() {
        
    }
    
    private func handleSubmit() {
        
    }
    
    var body: some View {
        VStack {
            Title(
                "Enter OTP",
                subtitle: "A 4-digit code has been sent to your email",
                alignment: .leading,
                showBackButton: true,
                backButtonAction: handleBackPress
            )
            
            VStack {
                CustomTextField(
                    "Email or Username",
                    text: $username,
                )
            }
            .padding(.horizontal, AppSpacing.Semantic.screen)
            .padding(.bottom, AppSpacing.Semantic.element)
            
            Spacer()
            
            NavigationLink(destination: ForgotPasswordView().navigationBarBackButtonHidden(true)) {
                Text("Submit")
                    .font(.headline)
                    .fontWeight(.bold)
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .frame(height: AppSizing.Semantic.button)
                    .background(Color.blue)
                    .cornerRadius(AppRadius.Semantic.button)
            }
            .padding(.horizontal, AppSpacing.Semantic.screen)
            .padding(.bottom, AppSpacing.Semantic.screen)
        }
    }
}

#Preview {
    OTPView()
}
