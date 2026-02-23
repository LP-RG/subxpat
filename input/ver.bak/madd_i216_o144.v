module madd_i216_o144 (a, b, c, r);
input [71:0] a,b,c;
output [143:0] r;

assign r = (a * b) + c;

endmodule
