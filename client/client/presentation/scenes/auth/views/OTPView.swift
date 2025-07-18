import SwiftUI

struct OTPView: View {
    @Environment(\.presentationMode) var presentationMode
    @State private var otpCode: String = ""
    
    private func handleBackPress() {
        presentationMode.wrappedValue.dismiss()
    }
    
    private func handleSubmit() {
        print("OTP submitted: \(otpCode)")
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
                    "4-Digit Code",
                    text: $otpCode,
                    keyboardType: .numberPad
                )
            }
            .padding(.horizontal, AppSpacing.Semantic.screen)
            .padding(.bottom, AppSpacing.Semantic.element)
            
            Spacer()
            
            NavigationLink(destination: PasswordChangeView().navigationBarBackButtonHidden(true)) {
                Text("Verify")
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
