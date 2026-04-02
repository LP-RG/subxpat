module mul_i104_o104 (a, b, r);
input [51:0] a,b;
output [103:0] r;

assign r = a * b;

endmodule
