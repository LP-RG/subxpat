module abs_diff_i604_o302(a,b,r);
input [301:0] a,b;
output [301:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
