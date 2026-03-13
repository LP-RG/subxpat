module top(a, b, c);
input [2:0]a;
input [2:0]b;
output [5:0]c;
assign c = a * b;
endmodule
