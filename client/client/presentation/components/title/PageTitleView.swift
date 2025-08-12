import SwiftUI

struct PageTitleView: View {
    var title: String
    
    var body: some View {
        Text(title)
            .font(Typography.largeTitle)
            .frame(maxWidth: .infinity, alignment: .leading)
    }
}

#Preview {
    PageTitleView(title: "Test Title")
}
