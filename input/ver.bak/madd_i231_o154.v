module madd_i231_o154 (a, b, c, r);
input [76:0] a,b,c;
output [153:0] r;

assign r = (a * b) + c;

endmodule
