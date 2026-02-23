module madd_i378_o252 (a, b, c, r);
input [125:0] a,b,c;
output [251:0] r;

assign r = (a * b) + c;

endmodule
