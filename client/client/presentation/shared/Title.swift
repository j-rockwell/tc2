import SwiftUI

struct Title: View {
    let title: String
    let subtitle: String?
    let alignment: HorizontalAlignment
    let showBackButton: Bool
    let backButtonAction: (() -> Void)?
    
    init(
        _ title: String,
        subtitle: String? = nil,
        alignment: HorizontalAlignment = .leading,
        showBackButton: Bool = false,
        backButtonAction: (() -> Void)? = nil,
    ) {
        self.title = title
        self.subtitle = subtitle
        self.alignment = alignment
        self.showBackButton = showBackButton
        self.backButtonAction = backButtonAction
    }
    
    var body: some View {
        VStack(alignment: alignment, spacing: 0) {
            HStack(alignment: .firstTextBaseline) {
                VStack(alignment: .leading, spacing: AppSpacing.xs) {
                    Text(title)
                        .font(.largeTitle)
                        .fontWeight(.semibold)
                    
                    if let subtitle = subtitle {
                        Text(subtitle)
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    }
                }
                
                Spacer()
                
                if showBackButton {
                    Button(action: backButtonAction ?? {}) {
                        Image(systemName: "xmark.circle.fill")
                            .font(.system(size: 28, weight: .medium))
                            .foregroundColor(.secondary)
                            .background(Color(.systemBackground))
                            .clipShape(Circle())
                    }
                    .offset(y: -4)
                }
            }
        }
        .padding(.top, AppSpacing.sm)
        .padding(.horizontal, AppSpacing.lg)
    }
}
