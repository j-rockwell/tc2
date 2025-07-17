import SwiftUI

struct AuthFlowView: View {
    var body: some View {
        NavigationView {
            VStack(spacing: 40) {
                Spacer()
                
                VStack(spacing: 24) {
                    Image(systemName: "figure.strengthtraining.traditional")
                        .font(.system(size: 80))
                        .foregroundColor(.blue)
                    
                    VStack(spacing: 8) {
                        Text("Training Club")
                            .font(.largeTitle)
                            .fontWeight(.bold)
                        
                        Text("Fitness with Friends")
                            .font(.headline)
                            .foregroundColor(.secondary)
                    }
                }
                
                Spacer()
                
                VStack(spacing: AppSpacing.Semantic.element) {
                    NavigationLink(destination: RegisterView().navigationBarBackButtonHidden(true)) {
                        Text("Create Account")
                            .font(.headline)
                            .fontWeight(.bold)
                            .foregroundColor(.white)
                            .frame(maxWidth: .infinity)
                            .frame(height: AppSizing.Semantic.button)
                            .background(Color.blue)
                            .cornerRadius(AppRadius.Semantic.button)
                    }
                    
                    NavigationLink(destination: LoginView().navigationBarBackButtonHidden(true)) {
                        Text("Continue with Email")
                            .font(.headline)
                            .fontWeight(.bold)
                            .foregroundColor(.white)
                            .frame(maxWidth: .infinity)
                            .frame(height: AppSizing.Semantic.button)
                            .background(Color.gray)
                            .cornerRadius(AppRadius.Semantic.button)
                    }
                }
            }
            .padding(.horizontal, 24)
            .navigationBarHidden(true)
        }
    }
}

#Preview {
    AuthFlowView()
}
