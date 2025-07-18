
import SwiftUI

struct ForgotPasswordView: View {
    @Environment(\.presentationMode) var presentationMode
    @State private var username: String = ""
    
    private func handleBackPress() {
        presentationMode.wrappedValue.dismiss()
    }
    
    private func handleSubmit() {
        print("Submit pressed with username: \(username)")
    }
    
    var body: some View {
        VStack {
            Title(
                "Forgot Password",
                alignment: .leading,
                showBackButton: true,
                backButtonAction: handleBackPress
            )
            
            VStack {
                CustomTextField(
                    "Email or Username",
                    text: $username,
                )
            }.padding(.horizontal, AppSpacing.Semantic.screen)
            
            Spacer()
            
            NavigationLink(destination: OTPView().navigationBarBackButtonHidden(true)) {
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
        .navigationBarHidden(true)
    }
}
