module madd_i528_o352 (a, b, c, r);
input [175:0] a,b,c;
output [351:0] r;

assign r = (a * b) + c;

endmodule
