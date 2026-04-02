module madd_i75_o50 (a, b, c, r);
input [24:0] a,b,c;
output [49:0] r;

assign r = (a * b) + c;

endmodule
