module mul_i4608_o4608 (a, b, r);
input [2303:0] a,b;
output [4607:0] r;

assign r = a * b;

endmodule
