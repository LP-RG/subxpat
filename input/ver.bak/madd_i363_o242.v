module madd_i363_o242 (a, b, c, r);
input [120:0] a,b,c;
output [241:0] r;

assign r = (a * b) + c;

endmodule
