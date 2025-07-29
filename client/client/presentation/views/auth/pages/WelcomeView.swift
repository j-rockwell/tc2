import SwiftUI

struct WelcomeView: View {
    var body: some View {
        VStack {
            Spacer()
            
            Text("Training Club")
                .font(.largeTitle)
                .fontWeight(.bold)
            
            Spacer()
            
            VStack(spacing: Spacing.Semantic.buttonGroup) {
                NavigationLink("Sign in", value: AuthFlowView.AuthView.login)
                    .buttonStyle(PrimaryButtonStyle())
                
                NavigationLink("Create Account", value: AuthFlowView.AuthView.register)
                    .buttonStyle(SecondaryButtonStyle())
            }
        }.padding()
    }
}

#Preview {
    WelcomeView()
}
