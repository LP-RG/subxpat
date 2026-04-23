module mul_i8_o8 (a, b, r);
input [3:0] a,b;
output [7:0] r;

assign r = a * b;

endmodule
