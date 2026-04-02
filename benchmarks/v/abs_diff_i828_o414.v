module abs_diff_i828_o414(a,b,r);
input [413:0] a,b;
output [413:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
