//
//  PasswordChangeView.swift
//  client
//
//  Created by John Rockwell on 7/18/25.
//

import SwiftUI

struct PasswordChangeView: View {
    @State private var password: String = ""
    @State private var confirmedPassword: String = ""
    
    private func handleBackPress() {
        
    }
    
    private func handleSubmit() {
        
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
    PasswordChangeView()
}
