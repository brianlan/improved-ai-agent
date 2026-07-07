export default {
  id: "strip-max-tokens",
  async server() {
    return {
      async "chat.params"(input, output) {
        // 只对 photonmark 这一家去掉 max_output_tokens
        if (input.provider.id === "photonmark") {
          output.maxOutputTokens = undefined
        }
      },
    }
  },
}
