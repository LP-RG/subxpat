module mul_i768_o768 (a, b, r);
input [383:0] a,b;
output [767:0] r;

assign r = a * b;

endmodule
