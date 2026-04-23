module madd_i24576_o16384 (a, b, c, r);
input [8191:0] a,b,c;
output [16383:0] r;

assign r = (a * b) + c;

endmodule
