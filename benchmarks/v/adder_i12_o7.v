module top(a, b, c);
input [5:0]a;
input [5:0]b;
output [6:0]c;

assign c = a + b;

endmodule