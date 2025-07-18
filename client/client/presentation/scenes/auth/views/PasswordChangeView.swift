import SwiftUI

struct PasswordChangeView: View {
    @Environment(\.presentationMode) var presentationMode
    @State private var password: String = ""
    @State private var confirmedPassword: String = ""
    
    private func handleBackPress() {
        presentationMode.wrappedValue.dismiss()
    }
    
    private func handleSubmit() {
        if password == confirmedPassword {
            print("Password changed successfully")
        } else {
            print("Passwords don't match")
        }
    }
    
    var body: some View {
        VStack {
            Title(
                "New Password",
                alignment: .leading,
                showBackButton: true,
                backButtonAction: handleBackPress
            )
            
            VStack(spacing: AppSpacing.Semantic.input) {
                CustomTextField(
                    "New Password",
                    text: $password,
                    isSecure: true
                )
                
                CustomTextField(
                    "Confirm Password",
                    text: $confirmedPassword,
                    isSecure: true
                )
            }.padding(.horizontal, AppSpacing.Semantic.screen)
            
            Spacer()
            
            Button(action: handleSubmit) {
                Text("Change Password")
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
