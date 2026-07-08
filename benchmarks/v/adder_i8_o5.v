module top(a, b, c);
input [3:0]a;
input [3:0]b;
output [4:0]c;

assign c = a + b;

endmodule