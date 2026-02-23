module abs_diff_i780_o390(a,b,r);
input [389:0] a,b;
output [389:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
