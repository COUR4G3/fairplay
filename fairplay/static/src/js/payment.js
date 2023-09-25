if (window.PaymentRequest) {

}

function buildSupportedPaymentMethodData() {
  return [{ supportedMethods: "https://example.com/pay" }];
}

function buildShoppingCartDetails() {
  // Hardcoded for demo purposes:
  return {
    id: "order-123",
    displayItems: [
      {
        label: "Example item",
        amount: { currency: "USD", value: "1.00" },
      },
    ],
    total: {
      label: "Total",
      amount: { currency: "USD", value: "1.00" },
    },
  };
}

function buildShoppingCartStubDetails() {
  return 
}

function createPaymentRequest() {

}

function canMakePayment(paymentMethod) {
  const request = createPaymentRequest(
    [{ supportedMethods: paymentMethod }],
    { total: { label: "Stub", amount: { currency: "USD", value: "0.01" } }},
  );

  return request.canMakePayment();
}
